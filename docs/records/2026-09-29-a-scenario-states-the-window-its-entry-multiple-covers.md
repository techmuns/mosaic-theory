---
id: 2026-09-29-a-scenario-states-the-window-its-entry-multiple-covers
status: shipped
date: 2026-09-29
prs: [658]
supersedes:
superseded-by:
---

# A scenario states the window its entry multiple covers

**WHAT.** A scenario record stores `spot` (a price) and each leg's exit multiple and denominator.
It never stored an ENTRY multiple, so any entry-to-exit comparison lived in the leg's `reason`
prose where nothing could check it. GOOGL's bear leg reads *"Bear EPS EXCEEDS today's NTM $13.29,
so the downside is multiple compression from ~26x"* — an NTM entry denominator against an exit leg
whose own year is unstated, and 339.35 ÷ 13.29 = 25.5x confirms the ~26x is NTM-struck. A return
described as compression when the two multiples sit on different windows is not measuring
compression, and no guard could say so while the entry window was unwritten.

Three changes, in the sequence the operator asked for:

1. **`ScenarioRecord.entry_basis`** — the PERIOD the entry multiple's denominator covers ("NTM",
   "LTM", "FY2026"). Not `multiple_basis`, which names the METRIC; this names the WINDOW.
2. **`leg_fy_problems(..., require_stated=True)`** — the write boundary may now require the base
   leg's fiscal year. The default stays permissive.
3. **`basis_problems`** — entry and exit must cover the same period, or the leg must bridge them.

**WHY THE ESCAPE HATCH IS NOT "ANY NON-BLANK REASON", WHICH IS THE FINDING WORTH KEEPING.**
`leg_fy_problems` already claimed to "refuse an unexplained disagreement", escaping on any
non-blank `reason`. **That refusal is unreachable.** `ScenarioInput` validates `reason` as required
and non-blank — `''`, `'   '` and `None` are all refused — so the guard's final branch fires only
in a state the constructor forbids. Its own pin reaches it through `model_copy`, which skips
validators. A guard whose escape hatch is satisfied by every legal input is not a guard.

So `basis_problems` excuses a mismatch only for a reason NAMING BOTH PERIODS — the bridge the
mismatch requires anyway, unsatisfiable by boilerplate, and deterministic. The dead branch in
`leg_fy_problems` is left alone deliberately: changing it would newly refuse existing records on
supersede, which is an operator's call and not this build's.

**HOW VERIFIED.**

*The corpus, for the field's cost.* All nine committed records round-trip BYTE-IDENTICAL — the
absent-vs-null rule `leg_fy` follows, verified against the records rather than assumed.
`scenarios/_schema.json` regenerates to carry the field, which is the only committed artifact that
moves.

*The write boundary, over the live corpus.* Every one of the nine would now be refused on a
supersede — seven for both fields, EPAM and GOOGL for `entry_basis` alone. That is the intended
effect of "a record written today states its basis", and it is a real friction cost stated here
rather than discovered later.

*Mutation — six, all caught, one survived first.* B1 the field serialising as null (churns all
nine); B2 the escape hatch becoming "any non-blank reason" — THE DEAD-GUARD DEFECT, reproduced
deliberately; B3 the mismatch never refusing; B4 `require_stated` ignored on the entry window;
B5 ignored on the leg year; B6 a free-text window accepted. **B4 SURVIVED the first round**: the
pins covered `require_stated` for the leg YEAR and never for the entry WINDOW, so disabling the
window's refusal left every test green. One half of a two-part gate, pinned; the other half not.

**BOUNDARY.** Measured 2026-09-29 off `55b791e9`. *9 records round-trip / 9 would be refused on
supersede / 7 lack `leg_fy`*: population = `scenarios/*.json` excluding the `_`-prefixed schema,
index and seal; unit = records. *25.5x*: GOOGL's `spot` 339.35 ÷ the NTM 13.29 its own bear
`reason` states.

**WHAT IT COSTS / WHAT IS ACCEPTED.**

- **EVERY EXISTING RECORD IS REFUSED ON ITS NEXT SUPERSEDE** until two short fields are added.
  Accepted because the repo already holds that every count states its boundary — window, filter,
  population, unit — and a multiple's denominator window is exactly that. The cost is one string
  per write; the thought it forces is the point.
- **`leg_fy_problems`' dead branch is not fixed here.** It still claims to refuse an unexplained
  disagreement and cannot. Fixing it would newly refuse committed records on supersede — an
  operator decision. *Falsifier:* a record superseded with a mismatched, unexplained `leg_fy` and
  no refusal.
- **Nothing computes an entry multiple.** This makes the basis STATABLE and CHECKABLE; it does not
  decompose a return into denominator roll versus re-rating. That is the piece a reviewer actually
  asked for and it is not built.
- **`basis_problems` compares WINDOWS, not values.** "NTM" against "FY2027" is refused as
  unbridged even where the two genuinely coincide at the exit date; the bridge sentence is how the
  analyst says so.
